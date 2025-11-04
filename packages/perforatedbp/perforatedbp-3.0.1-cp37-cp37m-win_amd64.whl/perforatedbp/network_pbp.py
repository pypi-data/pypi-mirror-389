from perforatedai import globals_perforatedai as GPA
from perforatedai import utils_perforatedai as UPA
import sys

from safetensors.torch import load_file
import copy

import torch.nn as nn
import torch
import pdb

from threading import Thread


doing_threading = False
loaded_full_print = False


def convert_module(net, depth, name_so_far):
    if type(net) is PAIModulePyThread:
        print(
            "Something in your model is pointed to twice by two different variables. Skipping second instance"
        )
        print(net)
        return net

    all_members = net.__dir__()
    # If this module is a Module List or Sequential go through each module
    if issubclass(type(net), nn.Sequential) or issubclass(type(net), nn.ModuleList):
        for submodule_id, layer in net.named_children():
            sub_name = name_so_far + "." + str(submodule_id)
            if sub_name in GPA.pc.get_module_ids_to_track():
                continue
            # If it has a substitution in modules_to_replace make that substitution
            if type(net.get_submodule(submodule_id)) in GPA.pc.get_modules_to_replace():
                setattr(
                    net,
                    submodule_id,
                    UPA.replace_predefined_modules(
                        net.get_submodule(submodule_id),
                        UPA.get_pretrained_pai_var(submodule_id),
                    ),
                )
            # If it is set as a module to convert make the conversion
            if (
                type(net.get_submodule(submodule_id)) in GPA.pc.get_modules_to_convert()
                or type(net.get_submodule(submodule_id)).__name__
                in GPA.pc.get_module_names_to_convert()
            ):
                setattr(
                    net,
                    submodule_id,
                    PAIModulePyThread(
                        net.get_submodule(submodule_id),
                        name_so_far + "." + str(submodule_id),
                    ),
                )
            # Otherwise check the module recursively if there are other modules to convert
            else:
                if net != net.get_submodule(submodule_id):
                    setattr(
                        net,
                        submodule_id,
                        convert_module(
                            net.get_submodule(submodule_id),
                            depth + 1,
                            name_so_far + "." + str(submodule_id),
                        ),
                    )
    # If the module is listed in ones to skip just continue
    elif type(net) in GPA.pc.get_modules_to_track():
        return net
    # If it is neither a sequential nor a skipped module must check conversion for each member variable
    else:
        for member in all_members:
            sub_name = name_so_far + "." + member
            if sub_name in GPA.pc.get_module_ids_to_track():
                continue
            # If it has a substitution in modules_to_replace make that substitution
            if type(getattr(net, member, None)) in GPA.pc.get_modules_to_replace():
                setattr(
                    net,
                    member,
                    UPA.replace_predefined_modules(getattr(net, member, None)),
                )
            # If it is set as a module to convert make the conversion
            if (
                type(getattr(net, member, None)) in GPA.pc.get_modules_to_convert()
                or type(getattr(net, member, None)).__name__
                in GPA.pc.get_module_names_to_convert()
            ):
                setattr(
                    net,
                    member,
                    PAIModulePyThread(getattr(net, member), name_so_far + "." + member),
                )
            # Otherwise, if it is a module, check the module recursively if there are other modules to convert
            elif issubclass(type(getattr(net, member, None)), nn.Module):
                if net != getattr(net, member):
                    setattr(
                        net,
                        member,
                        convert_module(
                            getattr(net, member), depth + 1, name_so_far + "." + member
                        ),
                    )
    return net


def convert_network(net, layer_name=""):
    # If the net itself has a substitution make that substitution first
    if type(net) in GPA.pc.get_modules_to_replace():
        net = UPA.replace_predefined_modules(net)
    # If the net itself should be converted make the converstion
    if type(net) in GPA.pc.get_modules_to_convert():
        if layer_name == "":
            print(
                "converting a single layer without a name, add a layer_name param to the call"
            )
            sys.exit(-1)
        net = PAIModulePyThread(net, layer_name)
    # Otherwise, check the module recursively if there are other modules to convert
    else:
        print("starting main call")
        net = convert_module(net, 0, ".")
    return net


def get_pai_modules(net, depth):
    all_members = net.__dir__()
    this_list = []
    if issubclass(type(net), nn.Sequential) or issubclass(type(net), nn.ModuleList):
        for submodule_id, layer in net.named_children():
            if net.get_submodule(submodule_id) is net:
                continue
            if type(net.get_submodule(submodule_id)) is PAIModulePyThread:
                this_list = this_list + [net.get_submodule(submodule_id)]
            else:
                this_list = this_list + get_pai_modules(
                    net.get_submodule(submodule_id), depth + 1
                )
    else:
        for member in all_members:
            if getattr(net, member, None) is net:
                continue
            if type(getattr(net, member, None)) is PAIModulePyThread:
                this_list = this_list + [getattr(net, member)]
            elif issubclass(type(getattr(net, member, None)), nn.Module):
                this_list = this_list + get_pai_modules(getattr(net, member), depth + 1)
    return this_list


def load_pai_model(net, filename):
    net = convert_network(net)
    state_dict = load_file(filename)
    pai_modules = get_pai_modules(net, 0)
    if pai_modules == []:
        print("No PAI modules were found something went wrong with convert network")
        sys.exit()
    for module in pai_modules:
        # Set up name to be what will be saved in the state dict
        module_name = module.name
        # First part of name is always . so remove that
        if module_name[:2] == "..":
            # strip "."
            module_name = module_name[2:]
        # If it was a dataparallel also remove 'module' from the name
        if module_name[:6] == "module":
            # strip the "module."
            module_name = module_name[7:]
        # Then instantiate as many Dendrites as were created during training
        num_cycles = int(state_dict[module_name + ".num_cycles"].item())
        # extract node index from state_dict
        nodeCount = 10
        # also extract view tuple
        if num_cycles > 0:
            module.simulate_cycles(num_cycles, nodeCount)
        if not module.processor is None:
            processor = copy.deepcopy(module.processor)
            processor.pre = module.processor.post_n1
            processor.post = module.processor.post_n2
            module.processor_array.append(processor)
        else:
            module.processor_array.append(None)
        buffer = nn.Parameter(
            torch.randn(state_dict[module_name + ".skip_weights"].shape)
        )
        module.register_parameter("skip_weights", buffer)
        # module.register_buffer('skip_weights', torch.zeros(state_dict[module_name + '.skip_weights'].shape))
        module.register_buffer("module_id", state_dict[module_name + ".module_id"])
        module.register_buffer("view_tuple", state_dict[module_name + ".view_tuple"])

    net.load_state_dict(state_dict)
    return net
    # figure out if doing this 'thread' stuff is actually helping at all.
    # If its not just get rid of it to simplify things.
    # to test this will have to first get load_pai_model actually set up and working then run a test with and #without threading.


class PAIModulePyThread(nn.Module):
    def __init__(self, original_module, name):
        super(PAIModulePyThread, self).__init__()
        self.name = name
        self.register_buffer("node_index", torch.tensor(-1))
        self.register_buffer("module_id", torch.tensor(-1))
        self.register_buffer("num_cycles", torch.tensor(-1))
        self.register_buffer("view_tuple", torch.tensor(-1))
        self.processor_array = []
        self.processor = None
        self.layer_array = nn.ModuleList([original_module])
        self.layer_array[-1].register_buffer("module_id", torch.tensor(-1))

        # If this original module has processing functions save the processor
        if type(original_module) in GPA.pc.get_modules_with_processing():
            module_index = GPA.pc.get_modules_with_processing().index(
                type(original_module)
            )
            self.processor = GPA.pc.get_modules_processing_classes()[module_index]()
        elif (
            type(original_module).__name__ in GPA.pc.get_module_names_with_processing()
        ):
            module_index = GPA.pc.get_module_names_with_processing().index(
                type(original_module).__name__
            )
            self.processor = GPA.pc.get_module_by_name_processing_classes()[
                module_index
            ]()
        self.register_buffer("module_id", torch.tensor(0))

    def simulate_cycles(self, num_cycles, nodeCount):
        for i in range(0, num_cycles, 2):
            self.layer_array.append(copy.deepcopy(self.layer_array[0]))
            self.layer_array[-1].register_buffer("module_id", torch.tensor(-1))
            if not self.processor is None:
                processor = copy.deepcopy(self.processor)
                processor.pre = self.processor.pre_d
                processor.post = self.processor.post_d
                self.processor_array.append(processor)
            else:
                self.processor_array.append(None)

    def process_and_forward(self, *args2, **kwargs2):
        c = args2[0]
        dendrite_outs = args2[1]
        args2 = args2[2:]
        if self.processor_array[c] != None:
            out_values = self.processor_array[c].pre(*args2, **kwargs2)
        out_values = self.layer_array[c](*args2, **kwargs2)
        if self.processor_array[c] != None:
            out = self.processor_array[c].post(out_values)
        else:
            out = out_values
        dendrite_outs[c] = out

    def process_and_pre(self, *args, **kwargs):
        dendrite_outs = args[0]
        args = args[1:]
        out = self.layer_array[-1].forward(*args, **kwargs)
        if not self.processor_array[-1] is None:
            out = self.processor_array[-1].pre(out)
        dendrite_outs[len(self.layer_array) - 1] = out

    def forward(self, *args, **kwargs):
        # this is currently false anyway, just remove the doing multi idea
        doing_multi = doing_threading
        dendrite_outs = [None] * len(self.layer_array)
        threads = {}
        for c in range(0, len(self.layer_array) - 1):
            args2, kwargs2 = args, kwargs
            if doing_multi:
                threads[c] = Thread(
                    target=self.process_and_forward,
                    args=(c, dendrite_outs, *args),
                    kwargs=kwargs,
                )
            else:
                self.process_and_forward(c, dendrite_outs, *args2, **kwargs2)
        if doing_multi:
            threads[len(self.layer_array) - 1] = Thread(
                target=self.process_and_pre, args=(dendrite_outs, *args), kwargs=kwargs
            )
        else:
            self.process_and_pre(dendrite_outs, *args, **kwargs)
        if doing_multi:
            for i in range(len(dendrite_outs)):
                threads[i].start()
            for i in range(len(dendrite_outs)):
                threads[i].join()
        for out_index in range(0, len(self.layer_array)):
            current_out = dendrite_outs[out_index]

            if len(self.layer_array) > 1:
                for in_index in range(0, out_index):
                    current_out = (
                        current_out
                        + self.skip_weights[out_index][in_index, :]
                        .view(self.view_tuple.tolist())
                        .to(current_out.device)
                        * dendrite_outs[in_index]
                    )
                if out_index < len(self.layer_array) - 1:
                    current_out = GPA.pc.get_pai_forward_function()(current_out)
            dendrite_outs[out_index] = current_out
        if not self.processor_array[-1] is None:
            current_out = self.processor_array[-1].post(current_out)
        return current_out
